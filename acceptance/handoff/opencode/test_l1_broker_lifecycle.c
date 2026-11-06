#include "l1_broker_lifecycle.h"

#include <assert.h>
#include <stdio.h>

static int64_t tick;
static int closes, reads, observes, consumes, stops, last_fd;
static int close_error, mismatch, late_consume, writer_open;

static int64_t now(void) { return tick; }
static int close_fd(int fd) { closes++; last_fd = fd; return close_error; }
static int stop_pidfd(int fd) { stops++; last_fd = fd; return 0; }

static int wait_event(int fd, bool consume, struct l1_event *event)
{
    last_fd = fd;
    *event = (struct l1_event){fd + 100, 1, consume && mismatch};
    if (consume) {
        consumes++;
        if (late_consume)
            tick = 7000 * L1_MS;
    } else {
        observes++;
    }
    return 0;
}

static long read_pipe(int fd, void *data, size_t capacity)
{
    (void)data;
    assert(fd == 21);
    if (++reads == 1) {
        assert(capacity == 513);
        return 4;
    }
    assert(capacity == 1);
    return writer_open ? -1 : 0;
}

static const struct l1_broker_io io = {now, close_fd, stop_pidfd, wait_event, read_pipe};

static struct l1_broker fresh(void)
{
    tick = 1000 * L1_MS;
    closes = reads = observes = consumes = stops = last_fd = 0;
    close_error = mismatch = late_consume = writer_open = 0;
    return (struct l1_broker){
        .slots = {{.pidfd = 17}, {.pidfd = 18}},
        .attempt = 4, .generation = 9, .deadline = 8000 * L1_MS,
    };
}

static void close_then_report(void)
{
    struct l1_broker b = fresh();
    struct l1_reader_report report = {0};
    assert(!l1_b_drain(&b, 21, &io) && !reads);
    close_error = 1;
    assert(!l1_e_release(22, (struct l1_reader_report){4, 9, true}, &report, &io));
    assert(!report.ready && !l1_b_accept(&b, report, &io));
    close_error = 0;
    assert(l1_e_release(22, (struct l1_reader_report){4, 9, true}, &report, &io));
    assert(closes == 2 && last_fd == 22 && l1_b_accept(&b, report, &io));
    assert(l1_b_drain(&b, 21, &io) && b.ready_reported && b.ready_eof && reads == 2);
    assert(!l1_b_drain(&b, 21, &io) && reads == 2);
}

static void e_loss_before_ready(void)
{
    struct l1_broker b = fresh();
    l1_b_e_loss(&b);
    assert(!l1_b_accept(&b, (struct l1_reader_report){4, 9, true}, &io));
    assert(!l1_b_drain(&b, 21, &io) && !reads);
    assert(l1_b_stop(&b, L1_H, &io) && stops == 1 && last_fd == 18);
    assert(!l1_b_stop(&b, L1_H, &io) && stops == 1);
    assert(l1_b_reap(&b, L1_E, &io) && last_fd == 17);
    assert(l1_b_drain(&b, 21, &io) && b.unknown && !b.ready_reported);
    assert(l1_b_reap(&b, L1_H, &io) && last_fd == 18);
    assert(observes == 2 && consumes == 2 && closes == 2);
}

static void unmatched_consume(void)
{
    struct l1_broker b = fresh();
    mismatch = 1;
    assert(!l1_b_reap(&b, L1_E, &io));
    assert(b.hold && !b.slots[L1_E].reaped && b.slots[L1_E].pidfd == 17);
    assert(!l1_b_drain(&b, 21, &io) && !l1_b_reap(&b, L1_E, &io));
    assert(consumes == 1 && closes == 0 && reads == 0);
}

static void consume_after_cutoff(void)
{
    struct l1_broker b = fresh();
    late_consume = 1;
    assert(!l1_b_reap(&b, L1_H, &io));
    assert(b.hold && b.slots[L1_H].pidfd == 18 && !closes);
    assert(!l1_b_stop(&b, L1_E, &io) && !l1_b_reap(&b, L1_E, &io));
    assert(!stops && consumes == 1);
}

static void ambiguous_birth(void)
{
    struct l1_broker b = fresh();
    b.slots[L1_H].pidfd = -1;
    l1_b_ambiguous_birth(&b);
    assert(b.unknown && b.hold);
    assert(!l1_b_stop(&b, L1_H, &io) && !l1_b_reap(&b, L1_H, &io));
    assert(!stops && !observes && !consumes);
    assert(l1_b_reap(&b, L1_E, &io) && b.hold);
}

static void retained_writer(void)
{
    struct l1_broker b = fresh();
    writer_open = 1;
    assert(l1_b_reap(&b, L1_E, &io));
    assert(!l1_b_drain(&b, 21, &io) && b.hold && !b.ready_eof);
    assert(!l1_b_drain(&b, 21, &io) && reads == 2);
}

static void deadline_with_missing_h(void)
{
    struct l1_broker b = fresh();
    assert(l1_b_reap(&b, L1_E, &io) && l1_b_drain(&b, 21, &io));
    tick = b.deadline;
    l1_b_finish_at_deadline(&b, true, &io);
    assert(b.hold && b.slots[L1_H].pidfd == 18);
}

int main(void)
{
    close_then_report();
    e_loss_before_ready();
    unmatched_consume();
    consume_after_cutoff();
    ambiguous_birth();
    retained_writer();
    deadline_with_missing_h();
    puts("7/7 mocked C broker lifecycle controls OK");
    return 0;
}
