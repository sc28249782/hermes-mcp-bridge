/* Pure readiness controls. This executable never invokes l1_start or l1_finish. */
#include "l1_retained.h"
#include <stdio.h>

int main(void)
{
    const struct l1_binding expected = {{1}, 7, 8, 8000 * L1_MS};
    const struct l1_ready valid = {
        expected, 3999 * L1_MS, 4001 * L1_MS, 2000 * L1_MS, L1_READY_MAGIC
    };
    const struct {
        const char *name;
        struct l1_ready ready;
        int64_t now;
        bool complete;
        bool live;
        bool accept;
    } cases[] = {
        {"valid", valid, 4500 * L1_MS, true, true, true},
        {"missing/extra/partial record", valid, 4500 * L1_MS, false, true, false},
        {"custody lost", valid, 4500 * L1_MS, true, false, false},
        {"late READY", valid, 5000 * L1_MS, true, true, false},
        {"wrong digest", {{{2}, 7, 8, 8000 * L1_MS}, 3999 * L1_MS,
                         4001 * L1_MS, 2000 * L1_MS, L1_READY_MAGIC},
         4500 * L1_MS, true, true, false},
        {"wrong generation", {{{1}, 7, 9, 8000 * L1_MS}, 3999 * L1_MS,
                              4001 * L1_MS, 2000 * L1_MS, L1_READY_MAGIC},
         4500 * L1_MS, true, true, false},
        {"expired/disarmed", {expected, 3999 * L1_MS, 4001 * L1_MS, 0, L1_READY_MAGIC},
         4500 * L1_MS, true, true, false},
        {"wrong target bracket", {expected, 3999 * L1_MS, 4001 * L1_MS,
                                  1900 * L1_MS, L1_READY_MAGIC},
         4500 * L1_MS, true, true, false},
        {"wide bracket", {expected, 3979 * L1_MS, 4001 * L1_MS,
                          2000 * L1_MS, L1_READY_MAGIC},
         4500 * L1_MS, true, true, false},
    };
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); i++) {
        if (l1_accept_ready(&expected, &cases[i].ready, cases[i].now,
                            cases[i].complete, cases[i].live) != cases[i].accept) {
            fprintf(stderr, "FAIL: %s\n", cases[i].name);
            return 1;
        }
    }
    puts("9/9 pure readiness controls OK");
    return 0;
}
