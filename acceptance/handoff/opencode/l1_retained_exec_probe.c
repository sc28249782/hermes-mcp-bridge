/* Inert fd-exec target. Deliberately linked without any E/H fixture source. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv, char **envp)
{
    if (argc != 2 || envp[0] != NULL)
        return 2;
    char *end;
    errno = 0;
    long image = strtol(argv[1], &end, 10);
    if (errno || end == argv[1] || *end || image < 3 || image > 1024)
        return 2;
    if (fcntl((int)image, F_GETFD) != -1 || errno != EBADF)
        return 4;
    for (int fd = 0; fd < 3; ++fd)
        if (fcntl(fd, F_GETFD) == -1)
            return 3;
    /* Low and high inherited sentinels are supplied by the parent controls. */
    const int sentinels[] = {3, 4, 127, 511};
    for (unsigned i = 0; i < sizeof(sentinels) / sizeof(sentinels[0]); ++i)
        if (fcntl(sentinels[i], F_GETFD) != -1 || errno != EBADF)
            return 4;
    static const char receipt[] = "L1_INERT_FD_EXEC\n";
    return write(STDOUT_FILENO, receipt, sizeof(receipt) - 1) ==
           (ssize_t)(sizeof(receipt) - 1) ? 0 : 5;
}
