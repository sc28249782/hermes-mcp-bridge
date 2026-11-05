#ifndef L1_RETAINED_ATTEMPT_H
#define L1_RETAINED_ATTEMPT_H

#include "l1_retained.h"

enum l1_attempt_result {
    L1_NOT_ADMITTED,
    L1_START_UNCONFIRMED,
    L1_STOP_UNCONFIRMED,
    L1_READY_REJECTED_REAPED,
    L1_READY_OBSERVED_REAPED,
};

struct l1_attempt {
    struct l1_owner owner;
    bool consumed;
    bool ready_observed;
    bool ready_eof;
};

/* Initialize once with {0}. Any remaining owner FDs belong to this same E.
 * This has no launcher or caller until E-loss containment is reviewed. */
enum l1_attempt_result l1_run_attempt(struct l1_attempt *attempt,
                                      const struct l1_binding *binding,
                                      int64_t t0, int64_t ta);

#endif
