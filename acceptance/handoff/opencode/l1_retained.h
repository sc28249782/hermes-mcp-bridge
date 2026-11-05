#ifndef L1_RETAINED_H
#define L1_RETAINED_H

#include <stdbool.h>
#include <stdint.h>

#define L1_MS INT64_C(1000000)
#define L1_READY_MAGIC UINT32_C(0x4c315244)

struct l1_binding {
    uint8_t source_digest[32];
    uint64_t attempt;
    uint64_t generation;
    int64_t deadline;
};

struct l1_ready {
    struct l1_binding binding;
    int64_t before;
    int64_t after;
    int64_t remaining;
    uint32_t magic;
};

struct l1_owner {
    int pidfd;
    int ready_read;
    int gate_write;
    int64_t deadline;
};

int64_t l1_now(void);
_Noreturn void l1_helper(int ready_write, int gate_read,
                         const struct l1_binding *binding);
bool l1_accept_ready(const struct l1_binding *expected,
                     const struct l1_ready *ready, int64_t now,
                     bool complete_and_eof, bool live_custody);
bool l1_start(struct l1_owner *owner, const struct l1_binding *binding);
bool l1_read_ready(const struct l1_owner *owner, const struct l1_binding *expected);
bool l1_finish(struct l1_owner *owner, bool *ready_eof);

#endif
