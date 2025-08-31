namespace Domain.Tickets;
//Provides a clear audit trail for each ticket, making it possible to later review changes, debugging, or analytics.
public sealed class TicketHistoryEntry
{
    public DateTime At { get; }
    public string Event { get; }
    public string? Notes { get; }

    public TicketHistoryEntry(string @event, string? notes = null, DateTime? at = null)
    {
        Event = @event;
        Notes = notes;
        At = at ?? DateTime.UtcNow;
    }
}

