#define _GNU_SOURCE
#include "l1_retained.h"

#include <fcntl.h>
#include <linux/sched.h>
#include <poll.h>
#include <signal.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

bool l1_accept_ready(const struct l1_binding *expected,
                     const struct l1_ready *ready, int64_t now,
                     bool complete_and_eof, bool live_custody)
{
    if (!complete_and_eof || !live_custody || ready->magic != L1_READY_MAGIC ||
        expected->deadline <= 3000 * L1_MS ||
        now < 0 || now >= expected->deadline - 3000 * L1_MS ||
        ready->before < 0 || ready->after < ready->before || ready->after > now ||
        ready->after - ready->before > 20 * L1_MS || ready->remaining <= 0 ||
        ready->binding.attempt != expected->attempt ||
        ready->binding.generation != expected->generation ||
        ready->binding.deadline != expected->deadline ||
        memcmp(ready->binding.source_digest, expected->source_digest, 32))
        return false;

    int64_t target = expected->deadline - 2000 * L1_MS;
    return target - ready->after <= ready->remaining &&
           ready->remaining <= target - ready->before;
}

/* Caller contract: dedicated single-threaded E, one attempt, closed inherited
 * FD inventory, reviewed exact binary, and deadline inherited from T0/Ta.
 * No caller or invocation is provided by this source-review packet. */
bool l1_start(struct l1_owner *owner, const struct l1_binding *binding)
{
    struct sigaction child;
    int ready[2], gate[2];
    int64_t now = l1_now();
    if (now < 0 || binding->deadline <= now ||
        binding->deadline - now <= 3000 * L1_MS ||
        binding->deadline - now > 20000 * L1_MS ||
        sigaction(SIGCHLD, NULL, &child) || child.sa_handler != SIG_DFL ||
        (child.sa_flags & SA_NOCLDWAIT) || pipe2(ready, O_CLOEXEC | O_NONBLOCK))
        return false;
    if (pipe2(gate, O_CLOEXEC)) {
        close(ready[0]);
        close(ready[1]);
        return false;
    }

    int pidfd = -1;
    struct clone_args args = {
        .flags = CLONE_PIDFD,
        .pidfd = (uintptr_t)&pidfd,
        .exit_signal = SIGCHLD,
    };
    long child_result = syscall(SYS_clone3, &args, sizeof(args));
    if (child_result == 0) {
        close(ready[0]);
        close(gate[1]);
        l1_helper(ready[1], gate[0], binding);
    }

    close(ready[1]);
    close(gate[0]);
    if (child_result < 0) {
        close(ready[0]);
        close(gate[1]);
        return false;
    }

    *owner = (struct l1_owner){pidfd, ready[0], gate[1], binding->deadline};
    return true;
}

static bool exited_by(int pidfd, int64_t cutoff)
{
    int64_t now = l1_now();
    if (now < 0 || now >= cutoff)
        return false;
    int64_t remaining = cutoff - now;
    struct timespec limit = {remaining / (1000 * L1_MS),
                             remaining % (1000 * L1_MS)};
    struct pollfd pollfd = {.fd = pidfd, .events = POLLIN};
    if (ppoll(&pollfd, 1, &limit, NULL) != 1 || !(pollfd.revents & POLLIN))
        return false;
    now = l1_now();
    return now >= 0 && now < cutoff;
}

/* READY is a single fixed record followed by EOF on the private channel. */
bool l1_read_ready(const struct l1_owner *owner, const struct l1_binding *expected)
{
    struct l1_ready ready = {0};
    unsigned char tail;
    struct pollfd fd = {.fd = owner->ready_read};
    int64_t now = l1_now();
    int64_t cutoff = owner->deadline - 3000 * L1_MS;
    if (now < 0 || now >= cutoff || owner->deadline != expected->deadline)
        return false;
    int64_t remaining = cutoff - now;
    struct timespec limit = {remaining / (1000 * L1_MS),
                             remaining % (1000 * L1_MS)};
    if (ppoll(&fd, 1, &limit, NULL) != 1 || !(fd.revents & POLLHUP) ||
        read(fd.fd, &ready, sizeof(ready)) != (ssize_t)sizeof(ready) ||
        read(fd.fd, &tail, 1) != 0)
        return false;

    siginfo_t status = {0};
    bool live = waitid(P_PIDFD, (id_t)owner->pidfd, &status,
                       WEXITED | WNOHANG | WNOWAIT) == 0 && status.si_pid == 0;
    return l1_accept_ready(expected, &ready, l1_now(), true, live);
}

static bool stop_by_pidfd(int pidfd, int64_t deadline)
{
    int64_t now = l1_now();
    if (now < 0 || deadline - now <= 1200 * L1_MS)
        return false;
    (void)syscall(SYS_pidfd_send_signal, pidfd, SIGTERM, NULL, 0);
    if (exited_by(pidfd, now + 200 * L1_MS))
        return true;

    now = l1_now();
    if (now < 0 || deadline - now <= 1000 * L1_MS)
        return false;
    (void)syscall(SYS_pidfd_send_signal, pidfd, SIGKILL, NULL, 0);
    return exited_by(pidfd, now + 1000 * L1_MS);
}

bool l1_finish(struct l1_owner *owner, bool *ready_eof)
{
    siginfo_t observed = {0}, consumed = {0};
    *ready_eof = false;
    if (owner->pidfd < 0)
        return false;
    if (owner->gate_write >= 0) {
        close(owner->gate_write);
        owner->gate_write = -1;
    }
    int64_t cutoff = owner->deadline - 500 * L1_MS;
    if (!exited_by(owner->pidfd, cutoff - 1300 * L1_MS) &&
        !stop_by_pidfd(owner->pidfd, cutoff))
        return false;
    if (waitid(P_PIDFD, (id_t)owner->pidfd, &observed, WEXITED | WNOHANG | WNOWAIT) ||
        observed.si_pid <= 0)
        return false;
    int64_t now = l1_now();
    if (now < 0 || now >= cutoff ||
        waitid(P_PIDFD, (id_t)owner->pidfd, &consumed, WEXITED | WNOHANG) ||
        consumed.si_pid != observed.si_pid || consumed.si_code != observed.si_code ||
        consumed.si_status != observed.si_status)
        return false;

    /* Only the matching consuming wait permits this pidfd close. */
    close(owner->pidfd);
    owner->pidfd = -1;
    unsigned char drain[sizeof(struct l1_ready) + 1];
    ssize_t count = read(owner->ready_read, drain, sizeof(drain));
    if (count == 0 || (count > 0 && count <= (ssize_t)sizeof(struct l1_ready) &&
                       read(owner->ready_read, drain, 1) == 0))
        *ready_eof = true;
    close(owner->ready_read);
    owner->ready_read = -1;
    now = l1_now();
    return now >= 0 && now < cutoff && *ready_eof;
}
