using Application.Ports;

namespace External;

public sealed class NoopExecutorAgent : IExecutorAgent
{
    public Task EmailChecklistAsync(string recipient, IReadOnlyList<string> steps, CancellationToken ct = default)
        => Task.CompletedTask;

    public Task NotifyApprovalAsync(string approverEmail, string ticketKey, string summary, CancellationToken ct = default)
        => Task.CompletedTask;
}