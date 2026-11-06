/* Executed only as a sealed test image. All lifecycle I/O is scripted. */
#define _POSIX_C_SOURCE 200809L
#include "l1_broker_lifecycle.h"

#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>

struct birth_receipt {
    enum l1_role role;
    uint64_t attempt;
    uint64_t generation;
    int original_pidfd;
};

static int64_t tick = 1000 * L1_MS;
static int calls;

static int64_t now(void) { return tick; }

static int close_fd(int fd)
{
    assert((calls == 3 && fd == 17) || (calls == 7 && fd == 18));
    calls++;
    return 0;
}

static int stop_pidfd(int fd)
{
    assert(calls++ == 0 && fd == 18);
    return 0;
}

static int wait_event(int fd, bool consume, struct l1_event *event)
{
    assert((fd == 17 && calls == (consume ? 2 : 1)) ||
           (fd == 18 && calls == (consume ? 6 : 5)));
    calls++;
    *event = (struct l1_event){fd + 100, 1, 0};
    return 0;
}

static long read_ready(int fd, void *bytes, size_t size)
{
    (void)bytes;
    assert(calls++ == 4 && fd == 21 && size == 513);
    return 0;
}

static const struct l1_broker_io io = {
    now, close_fd, stop_pidfd, wait_event, read_ready
};

static bool bind(struct l1_broker *b, enum l1_role expected, struct birth_receipt receipt)
{
    enum l1_role other = expected == L1_E ? L1_H : L1_E;
    if (b->unknown || b->hold || receipt.role != expected ||
        receipt.attempt != b->attempt || receipt.generation != b->generation ||
        receipt.original_pidfd < 0 || b->slots[expected].pidfd >= 0 ||
        b->slots[other].pidfd == receipt.original_pidfd) {
        l1_b_ambiguous_birth(b);
        return false;
    }
    b->slots[expected].pidfd = receipt.original_pidfd;
    return true;
}

static struct l1_broker fresh(void)
{
    return (struct l1_broker){
        .slots = {{.pidfd = -1}, {.pidfd = -1}},
        .attempt = 3, .generation = 5, .deadline = 8000 * L1_MS
    };
}

static void reject_bad_births(void)
{
    const struct birth_receipt invalid[] = {
        {L1_E, 3, 5, 18}, {L1_H, 4, 5, 18}, {L1_H, 3, 6, 18},
        {L1_H, 3, 5, 17}, {L1_H, 3, 5, -1},
    };
    for (size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); i++) {
        struct l1_broker b = fresh();
        assert(bind(&b, L1_E, (struct birth_receipt){L1_E, 3, 5, 17}));
        assert(!bind(&b, L1_H, invalid[i]));
        assert(b.hold && b.unknown && b.slots[L1_H].pidfd == -1);
        assert(!bind(&b, L1_H, (struct birth_receipt){L1_H, 3, 5, 18}));
        assert(!l1_b_stop(&b, L1_H, &io) && !l1_b_reap(&b, L1_H, &io));
        assert(calls == 0);
    }
}

static void run_loss_sequence(void)
{
    struct l1_broker b = fresh();
    assert(bind(&b, L1_E, (struct birth_receipt){L1_E, 3, 5, 17}));
    assert(bind(&b, L1_H, (struct birth_receipt){L1_H, 3, 5, 18}));
    l1_b_e_loss(&b);
    assert(!l1_b_accept(&b, (struct l1_reader_report){3, 5, true}, &io));
    assert(!l1_b_drain(&b, 21, &io));
    assert(l1_b_stop(&b, L1_H, &io));
    assert(l1_b_reap(&b, L1_E, &io));
    assert(l1_b_drain(&b, 21, &io));
    assert(l1_b_reap(&b, L1_H, &io));
    tick = b.deadline;
    l1_b_finish_at_deadline(&b, false, &io);
    assert(calls == 8 && b.unknown && b.hold && b.ready_eof);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    char *end;
    long image_fd = strtol(argv[1], &end, 10);
    assert(end != argv[1] && !*end && image_fd >= 3 && image_fd <= 1024);
    assert(fcntl((int)image_fd, F_GETFD) == -1 && errno == EBADF);
    reject_bad_births();
    run_loss_sequence();
    puts("L1_SEALED_C_BROKER_PREFLIGHT_HOLD");
    return 0;
}
