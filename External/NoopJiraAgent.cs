using Application.Ports;

namespace External;

public sealed class NoopJiraAgent : IJiraAgent
{
    public Task AddCommentAsync(string issueKey, string comment, CancellationToken ct = default)
        => Task.CompletedTask;

    public Task<string> CreateOrAttachAsync(string summary, string description, string priority, CancellationToken ct = default)
        => Task.FromResult($"IT-{Guid.NewGuid().ToString()[..6].ToUpper()}");

    public Task TransitionAsync(string issueKey, string transitionName, CancellationToken ct = default)
        => Task.CompletedTask;
}