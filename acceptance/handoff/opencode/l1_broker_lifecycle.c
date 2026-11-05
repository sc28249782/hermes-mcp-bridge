#include "l1_broker_lifecycle.h"

static bool before(const struct l1_broker *b, const struct l1_broker_io *io,
                   int64_t reserve)
{
    int64_t now = io->now();
    return now >= 0 && b->deadline > reserve && now < b->deadline - reserve;
}

bool l1_e_release(int fd, struct l1_reader_report report,
                  struct l1_reader_report *out, const struct l1_broker_io *io)
{
    if (io->close_fd(fd))
        return false;
    *out = report;
    return true;
}

bool l1_b_accept(struct l1_broker *b, struct l1_reader_report report,
                 const struct l1_broker_io *io)
{
    if (b->reader_released || b->unknown || b->hold ||
        report.attempt != b->attempt || report.generation != b->generation ||
        !before(b, io, 3000 * L1_MS))
        return false;
    b->reader_released = true;
    b->ready_reported = report.ready;
    return true;
}

void l1_b_e_loss(struct l1_broker *b)
{
    b->unknown = true;
    b->ready_reported = false;
}

void l1_b_ambiguous_birth(struct l1_broker *b)
{
    l1_b_e_loss(b);
    b->hold = true;
}

bool l1_b_stop(struct l1_broker *b, enum l1_role role, const struct l1_broker_io *io)
{
    if ((unsigned)role >= L1_ROLE_COUNT || b->slots[role].pidfd < 0 ||
        b->slots[role].consume_attempted || b->slots[role].stop_attempted || !before(b, io, 1000 * L1_MS))
        return false;
    b->slots[role].stop_attempted = true;
    return !io->stop_pidfd(b->slots[role].pidfd) && before(b, io, 1000 * L1_MS);
}

bool l1_b_reap(struct l1_broker *b, enum l1_role role, const struct l1_broker_io *io)
{
    if ((unsigned)role >= L1_ROLE_COUNT)
        return false;
    struct l1_slot *slot = &b->slots[role];
    struct l1_event observed = {0}, consumed = {0};
    if (slot->pidfd < 0 || slot->consume_attempted || !before(b, io, 1000 * L1_MS) ||
        io->wait_event(slot->pidfd, false, &observed) || observed.pid <= 0 ||
        !before(b, io, 1000 * L1_MS))
        return false;

    slot->consume_attempted = true;
    if (io->wait_event(slot->pidfd, true, &consumed) ||
        observed.pid != consumed.pid || observed.code != consumed.code ||
        observed.status != consumed.status || !before(b, io, 1000 * L1_MS)) {
        b->hold = true;
        return false;
    }
    slot->reaped = true;
    int pidfd = slot->pidfd;
    slot->pidfd = -1;
    if (io->close_fd(pidfd)) {
        b->hold = true;
        return false;
    }
    return true;
}

bool l1_b_drain(struct l1_broker *b, int ready_fd, const struct l1_broker_io *io)
{
    char discarded[513];
    if (b->drain_attempted || !(b->reader_released || b->slots[L1_E].reaped) ||
        !before(b, io, 500 * L1_MS))
        return false;
    b->drain_attempted = true;
    long bytes = io->read_nonblocking(ready_fd, discarded, sizeof(discarded));
    if (bytes > 0 && bytes <= 512 && before(b, io, 500 * L1_MS))
        bytes = io->read_nonblocking(ready_fd, discarded, 1);
    b->ready_eof = bytes == 0 && before(b, io, 500 * L1_MS);
    b->hold = b->hold || !b->ready_eof;
    return b->ready_eof;
}

void l1_b_finish_at_deadline(struct l1_broker *b, bool streams_eof,
                             const struct l1_broker_io *io)
{
    if (!before(b, io, 0) &&
        !(b->slots[L1_E].reaped && b->slots[L1_H].reaped && streams_eof && b->ready_eof))
        b->hold = true;
}
