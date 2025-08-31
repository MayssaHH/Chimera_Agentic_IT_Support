namespace Application.Ports;
public interface IExecutorAgent
{
    Task EmailChecklistAsync(string recipient, IReadOnlyList<string> steps, CancellationToken ct = default);
    Task NotifyApprovalAsync(string approverEmail, string ticketKey, string summary, CancellationToken ct = default);
}