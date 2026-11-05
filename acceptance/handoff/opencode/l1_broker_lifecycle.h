#ifndef L1_BROKER_LIFECYCLE_H
#define L1_BROKER_LIFECYCLE_H

#include "l1_retained.h"
#include <stddef.h>

enum l1_role { L1_E, L1_H, L1_ROLE_COUNT };

struct l1_event {
    int pid;
    int code;
    int status;
};

struct l1_slot {
    int pidfd; /* Fixture initializes unbound slots to -1. */
    bool stop_attempted;
    bool consume_attempted;
    bool reaped;
};

struct l1_reader_report {
    uint64_t attempt;
    uint64_t generation;
    bool ready;
};

struct l1_broker {
    struct l1_slot slots[L1_ROLE_COUNT];
    uint64_t attempt;
    uint64_t generation;
    int64_t deadline;
    bool reader_released;
    bool ready_reported;
    bool unknown;
    bool hold;
    bool drain_attempted;
    bool ready_eof;
};

/* Mock-only lifecycle seam. No production adapter or launch entry point. */
struct l1_broker_io {
    int64_t (*now)(void);
    int (*close_fd)(int);
    int (*stop_pidfd)(int);
    int (*wait_event)(int, bool consume, struct l1_event *);
    long (*read_nonblocking)(int, void *, size_t);
};

bool l1_e_release(int fd, struct l1_reader_report report,
                  struct l1_reader_report *out, const struct l1_broker_io *io);
bool l1_b_accept(struct l1_broker *b, struct l1_reader_report report,
                 const struct l1_broker_io *io);
void l1_b_e_loss(struct l1_broker *b);
void l1_b_ambiguous_birth(struct l1_broker *b);
bool l1_b_stop(struct l1_broker *b, enum l1_role role, const struct l1_broker_io *io);
bool l1_b_reap(struct l1_broker *b, enum l1_role role, const struct l1_broker_io *io);
bool l1_b_drain(struct l1_broker *b, int ready_fd, const struct l1_broker_io *io);

void l1_b_finish_at_deadline(struct l1_broker *b, bool streams_eof,
                             const struct l1_broker_io *io);

#endif
