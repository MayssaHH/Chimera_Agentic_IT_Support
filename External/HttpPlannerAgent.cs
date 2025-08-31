using Microsoft.Extensions.Configuration;

namespace External;

using System.Net.Http.Json;
using System.Text.Json;
using Application.Ports;


public class HttpPlannerAgent : IPlannerAgent
{
    private readonly HttpClient _http;
    private readonly IConfiguration _cfg;

    public HttpPlannerAgent(HttpClient http, IConfiguration cfg)
    {
        _http = http;
        _cfg = cfg;
    }

    public async Task<(IReadOnlyList<string>, IReadOnlyList<Citation>)> PlanAsync(string text, CancellationToken ct = default)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/plan")
        {
            Content = JsonContent.Create(new { text })
        };
        req.Headers.Add("x-api-key", _cfg["Agents:ApiKey"]);

        var res = await _http.SendAsync(req, ct);
        res.EnsureSuccessStatusCode();

        var json = await res.Content.ReadFromJsonAsync<JsonElement>(cancellationToken: ct);

        var steps = new List<string>();
        if (json.TryGetProperty("steps", out var sArr))
            steps.AddRange(sArr.EnumerateArray().Select(s => s.GetString() ?? ""));

        var citations = new List<Citation>();
        if (json.TryGetProperty("citations", out var cArr))
            foreach (var c in cArr.EnumerateArray())
                citations.Add(new Citation(
                    c.GetProperty("rule_id").GetString() ?? "",
                    c.GetProperty("title").GetString() ?? "",
                    c.TryGetProperty("url", out var u) && u.ValueKind != JsonValueKind.Null ? u.GetString() : null
                ));

        return (steps, citations);
    }
}
