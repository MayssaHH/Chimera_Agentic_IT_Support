namespace Application.Ports;

public interface IJiraAgent
{
    Task<string> CreateOrAttachAsync(string summary, string description, string priority, CancellationToken ct = default);
    Task TransitionAsync(string issueKey, string transitionName, CancellationToken ct = default);
    Task AddCommentAsync(string issueKey, string comment, CancellationToken ct = default);
}