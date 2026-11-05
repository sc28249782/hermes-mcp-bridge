#include "l1_retained_attempt.h"
#include <stdio.h>
#include <stdlib.h>

static int calls;
static bool start_ok, ready_ok, finish_ok;

int64_t l1_now(void) { return 1000 * L1_MS; }

bool l1_start(struct l1_owner *owner, const struct l1_binding *binding)
{
    if (calls++ != 0 || owner->pidfd != -1)
        abort();
    if (start_ok)
        *owner = (struct l1_owner){17, 18, 19, binding->deadline};
    return start_ok;
}

bool l1_read_ready(const struct l1_owner *owner, const struct l1_binding *binding)
{
    if (calls++ != 1 || owner->pidfd != 17 || owner->deadline != binding->deadline)
        abort();
    return ready_ok;
}

bool l1_finish(struct l1_owner *owner, bool *ready_eof)
{
    if (calls++ != 2 || owner->pidfd != 17)
        abort();
    owner->gate_write = -1;
    if (finish_ok) {
        owner->pidfd = owner->ready_read = -1;
        *ready_eof = true;
    }
    return finish_ok;
}

int main(void)
{
    const struct {
        int64_t deadline_ms;
        bool start, ready, finish;
        enum l1_attempt_result result;
        int expected_calls, expected_pidfd;
    } cases[] = {
        {4000, true, true, true, L1_NOT_ADMITTED, 0, 0},
        {9001, true, true, true, L1_NOT_ADMITTED, 0, 0},
        {9000, false, false, false, L1_START_UNCONFIRMED, 1, -1},
        {9000, true, true, false, L1_STOP_UNCONFIRMED, 3, 17},
        {9000, true, false, true, L1_READY_REJECTED_REAPED, 3, -1},
        {9000, true, true, true, L1_READY_OBSERVED_REAPED, 3, -1},
    };
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); i++) {
        struct l1_attempt attempt = {0};
        struct l1_binding binding = {.deadline = cases[i].deadline_ms * L1_MS};
        calls = 0;
        start_ok = cases[i].start;
        ready_ok = cases[i].ready;
        finish_ok = cases[i].finish;
        if (l1_run_attempt(&attempt, &binding, 0, 1000 * L1_MS) != cases[i].result ||
            calls != cases[i].expected_calls || attempt.owner.pidfd != cases[i].expected_pidfd ||
            attempt.ready_eof != (calls == 3 && finish_ok) ||
            l1_run_attempt(&attempt, &binding, 0, 1000 * L1_MS) != L1_NOT_ADMITTED ||
            calls != cases[i].expected_calls)
            return 1;
    }
    puts("6/6 mocked attempt controls OK");
    return 0;
}
