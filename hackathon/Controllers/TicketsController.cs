using Domain.Tickets;
using Persistence;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace hackathon.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TicketsController : ControllerBase
{
    private readonly AppDbContext _db;
    public TicketsController(AppDbContext db) => _db = db;

    [HttpGet]
    public async Task<IActionResult> List(CancellationToken ct)
    {
        var tickets = await _db.Tickets
            .OrderByDescending(t => t.Id)
            .Select(t => new {
                t.Id,
                t.Title,
                Status = t.Status.ToString(),
                t.JiraKey
            })
            .ToListAsync(ct);

        return Ok(tickets);
    }
}