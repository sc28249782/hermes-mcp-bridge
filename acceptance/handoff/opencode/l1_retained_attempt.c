#include "l1_retained_attempt.h"

enum l1_attempt_result l1_run_attempt(struct l1_attempt *attempt,
                                      const struct l1_binding *binding,
                                      int64_t t0, int64_t ta)
{
    if (attempt->consumed)
        return L1_NOT_ADMITTED;

    int64_t now = l1_now();
    if (now < 0 || t0 < 0 || ta < t0 || ta > now ||
        binding->deadline <= now ||
        binding->deadline - now <= 3000 * L1_MS ||
        binding->deadline - ta > 8000 * L1_MS ||
        binding->deadline - t0 > 45000 * L1_MS)
        return L1_NOT_ADMITTED;

    attempt->consumed = true;
    attempt->owner = (struct l1_owner){.pidfd = -1, .ready_read = -1, .gate_write = -1};
    if (!l1_start(&attempt->owner, binding))
        return L1_START_UNCONFIRMED;
    attempt->ready_observed = l1_read_ready(&attempt->owner, binding);
    if (!l1_finish(&attempt->owner, &attempt->ready_eof))
        return L1_STOP_UNCONFIRMED;
    return attempt->ready_observed ? L1_READY_OBSERVED_REAPED : L1_READY_REJECTED_REAPED;
}
