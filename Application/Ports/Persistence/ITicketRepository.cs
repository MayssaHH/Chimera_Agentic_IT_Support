namespace Application.Ports.Persistence;

using Domain.Tickets;

public interface ITicketRepository
{
    Task AddAsync(Ticket t, CancellationToken ct = default);
    Task<Ticket?> GetAsync(Guid id, CancellationToken ct = default);
    Task<IReadOnlyList<Ticket>> ListAsync(CancellationToken ct = default);
    Task SaveAsync(CancellationToken ct = default);
}
