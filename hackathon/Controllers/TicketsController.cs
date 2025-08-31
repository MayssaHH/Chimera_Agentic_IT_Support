using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Persistence;

namespace hackathon.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TicketsController : ControllerBase
{
    private readonly AppDbContext _db;

    public TicketsController(AppDbContext db) => _db = db;

    /// <summary>
    /// List all tickets (optionally filter by requester email)
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> List([FromQuery] string? email, CancellationToken ct)
    {
        var query = _db.Tickets.AsQueryable();

        if (!string.IsNullOrWhiteSpace(email))
            query = query.Where(t => t.RequesterEmail == email);

        var tickets = await query
            .OrderByDescending(t => t.Id)
            .Select(t => new
            {
                t.Id,
                t.Title,
                Status = t.Status.ToString(),
                t.JiraKey,
                t.RequesterEmail,
                t.Priority
            })
            .ToListAsync(ct);

        return Ok(tickets);
    }

    /// <summary>
    /// Get details of a single ticket by ID
    /// </summary>
    [HttpGet("{id:guid}")]
    public async Task<IActionResult> Get(Guid id, CancellationToken ct)
    {
        var t = await _db.Tickets.FirstOrDefaultAsync(x => x.Id == id, ct);
        if (t is null) return NotFound();

        // For now return ticket fields only.
        // Later you can enrich this with decision, checklist, citations, history.
        return Ok(new
        {
            t.Id,
            t.Title,
            t.Description,
            Status = t.Status.ToString(),
            t.JiraKey,
            t.RequesterEmail,
            t.Priority
        });
    }
}