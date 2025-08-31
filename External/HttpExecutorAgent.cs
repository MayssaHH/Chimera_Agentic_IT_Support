using System.Net.Http.Json;
using Application.Ports;

namespace External;

public sealed class HttpExecutorAgent : IExecutorAgent
{
    private readonly HttpClient _http;

    public HttpExecutorAgent(HttpClient http)
    {
        _http = http;
        _http.Timeout = TimeSpan.FromSeconds(10);
    }

    public async Task EmailChecklistAsync(string recipient, IReadOnlyList<string> steps, CancellationToken ct = default)
    {
        // POST /smtp/send-checklist { to, steps }
        var res = await _http.PostAsJsonAsync("/smtp/send-checklist", new { to = recipient, steps }, ct);
        res.EnsureSuccessStatusCode();
    }

    public async Task NotifyApprovalAsync(string approverEmail, string ticketKey, string summary, CancellationToken ct = default)
    {
        // POST /smtp/notify-approval { approverEmail, ticketKey, summary }
        var res = await _http.PostAsJsonAsync("/smtp/notify-approval", new { approverEmail, ticketKey, summary }, ct);
        res.EnsureSuccessStatusCode();
    }
}