#define _GNU_SOURCE
#include "l1_retained.h"

#include <signal.h>
#include <time.h>
#include <unistd.h>

static void expire(int signum)
{
    (void)signum;
    _exit(0);
}

static struct timespec to_timespec(int64_t ns)
{
    return (struct timespec){ns / INT64_C(1000000000), ns % INT64_C(1000000000)};
}

int64_t l1_now(void)
{
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) < 0)
        return -1;
    return (int64_t)t.tv_sec * INT64_C(1000000000) + t.tv_nsec;
}

_Noreturn void l1_helper(int ready_write, int gate_read,
                         const struct l1_binding *binding)
{
    struct sigaction action = {.sa_handler = expire};
    struct sigaction observed;
    sigset_t expiry, mask;
    struct sigevent event = {.sigev_notify = SIGEV_SIGNAL, .sigev_signo = SIGALRM};
    struct itimerspec setting = {.it_value = to_timespec(binding->deadline - 2000 * L1_MS)};
    struct itimerspec remaining;
    struct l1_ready ready = {0};
    timer_t timer;
    char byte;

    if (sigemptyset(&action.sa_mask) || sigemptyset(&expiry) ||
        sigaddset(&expiry, SIGALRM) || sigaction(SIGALRM, &action, NULL) ||
        sigprocmask(SIG_UNBLOCK, &expiry, NULL) ||
        sigaction(SIGALRM, NULL, &observed) || observed.sa_handler != expire ||
        sigprocmask(SIG_SETMASK, NULL, &mask) || sigismember(&mask, SIGALRM) != 0 ||
        timer_create(CLOCK_MONOTONIC, &event, &timer) ||
        timer_settime(timer, TIMER_ABSTIME, &setting, NULL))
        _exit(2);

    ready.before = l1_now();
    if (timer_gettime(timer, &remaining))
        _exit(2);
    ready.after = l1_now();
    if (ready.before < 0 || ready.after < ready.before ||
        remaining.it_interval.tv_sec || remaining.it_interval.tv_nsec)
        _exit(2);
    ready.remaining = (int64_t)remaining.it_value.tv_sec * INT64_C(1000000000)
                      + remaining.it_value.tv_nsec;
    ready.binding = *binding;
    ready.magic = L1_READY_MAGIC;
    if (write(ready_write, &ready, sizeof(ready)) != (ssize_t)sizeof(ready))
        _exit(2);
    if (close(ready_write))
        _exit(2);
    _exit(read(gate_read, &byte, 1) == 0 ? 0 : 2);
}
