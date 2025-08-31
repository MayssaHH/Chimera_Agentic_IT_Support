using System.Net.Http.Json;
using Application.Ports;

namespace External;

public sealed class HttpJiraAgent : IJiraAgent
{
    private readonly HttpClient _http;

    public HttpJiraAgent(HttpClient http)
    {
        _http = http;
        _http.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task<string> CreateOrAttachAsync(string summary, string description, string priority, CancellationToken ct = default)
    {
        // POST /jira/create { summary, description, priority } → { key: "IT-123" }
        var res = await _http.PostAsJsonAsync("/jira/create", new { summary, description, priority }, ct);
        res.EnsureSuccessStatusCode();

        var dto = await res.Content.ReadFromJsonAsync<CreateIssueDto>(cancellationToken: ct)
                  ?? throw new InvalidOperationException("Empty Jira response");
        return dto.Key;
    }

    public async Task TransitionAsync(string issueKey, string transitionName, CancellationToken ct = default)
    {
        // POST /jira/transition { key, transition }
        var res = await _http.PostAsJsonAsync("/jira/transition", new { key = issueKey, transition = transitionName }, ct);
        res.EnsureSuccessStatusCode();
    }

    public async Task AddCommentAsync(string issueKey, string comment, CancellationToken ct = default)
    {
        // POST /jira/comment { key, comment }
        var res = await _http.PostAsJsonAsync("/jira/comment", new { key = issueKey, comment }, ct);
        res.EnsureSuccessStatusCode();
    }

    private sealed record CreateIssueDto(string Key);
}