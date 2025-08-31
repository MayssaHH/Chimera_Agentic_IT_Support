using System.Net.Http.Json;
using System.Text.Json;
using Application.Ports;
using Microsoft.Extensions.Configuration;

namespace External;

public class HttpClassifierAgent : IClassifierAgent
{
    private readonly HttpClient _http;
    private readonly IConfiguration _cfg;

    public HttpClassifierAgent(HttpClient http, IConfiguration cfg)
    {
        _http = http;
        _cfg = cfg;
    }

    public async Task<(Decision, IReadOnlyList<Citation>)> ClassifyAsync(string text, CancellationToken ct = default)
    {
        var req = new HttpRequestMessage(HttpMethod.Post, "/classify")
        {
            Content = JsonContent.Create(new { text })
        };
        req.Headers.Add("x-api-key", _cfg["Agents:ApiKey"]);

        var res = await _http.SendAsync(req, ct);
        res.EnsureSuccessStatusCode();

        var json = await res.Content.ReadFromJsonAsync<JsonElement>(cancellationToken: ct);
        var decision = Enum.Parse<Decision>(json.GetProperty("decision").GetString()!, true);

        var citations = new List<Citation>();
        if (json.TryGetProperty("citations", out var arr))
        {
            foreach (var c in arr.EnumerateArray())
            {
                citations.Add(new Citation(
                    c.GetProperty("rule_id").GetString() ?? "",
                    c.GetProperty("title").GetString() ?? "",
                    c.TryGetProperty("url", out var u) && u.ValueKind != JsonValueKind.Null ? u.GetString() : null
                ));
            }
        }

        return (decision, citations);
    }
}