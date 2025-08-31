using Microsoft.AspNetCore.Mvc;
using Persistence;

namespace hackathon.Controllers;

[ApiController]
[Route("internal/health")]
[ApiExplorerSettings(IgnoreApi = true)]
public class HealthController : ControllerBase
{
    [HttpGet("api")]
    public async Task<IActionResult> Api([FromServices] AppDbContext db)
    {
        var can = await db.Database.CanConnectAsync();
        return Ok(new { ok = can });
    }

    [HttpGet("agents")]
    public IActionResult Agents([FromServices] IHttpClientFactory factory)
    {
        return Ok(new { ok = true }); // ping agents here if needed
    }
}
