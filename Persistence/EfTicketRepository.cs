using Application.Ports.Persistence;
using Domain.Tickets;
using Microsoft.EntityFrameworkCore;

namespace Persistence;

public class EfTicketRepository : ITicketRepository
{
    private readonly AppDbContext _db;
    public EfTicketRepository(AppDbContext db) => _db = db;

    public Task AddAsync(Ticket t, CancellationToken ct = default) =>
        _db.Tickets.AddAsync(t, ct).AsTask();

    public Task<Ticket?> GetAsync(Guid id, CancellationToken ct = default) =>
        _db.Tickets.FirstOrDefaultAsync(x => x.Id == id, ct);

    public async Task<IReadOnlyList<Ticket>> ListAsync(CancellationToken ct = default) =>
        await _db.Tickets.OrderByDescending(x => x.Id).ToListAsync(ct);

    public Task SaveAsync(CancellationToken ct = default) => _db.SaveChangesAsync(ct);
}