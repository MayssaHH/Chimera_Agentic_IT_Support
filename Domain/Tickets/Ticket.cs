namespace Domain.Tickets;

public sealed class Ticket
{
    public Guid Id { get; private set; } = Guid.NewGuid();
    public string Title { get; private set; }
    public string Description { get; private set; }
    public string RequesterEmail { get; private set; }
    public TicketStatus Status { get; private set; } = TicketStatus.New;
    public string Priority { get; private set; } = "normal";   // low|normal|high
    public string? JiraKey { get; private set; }

    private readonly List<TicketHistoryEntry> _history = new();
    public IReadOnlyList<TicketHistoryEntry> History => _history;

    private Ticket() { } 

    private Ticket(string title, string description, string requesterEmail, string priority)
    {
        Title = title.Trim();
        Description = description.Trim();
        RequesterEmail = requesterEmail.Trim().ToLowerInvariant();
        Priority = string.IsNullOrWhiteSpace(priority) ? "normal" : priority.ToLowerInvariant();

        _history.Add(new TicketHistoryEntry("CREATED"));
    }

    public static Ticket Create(string title, string description, string requesterEmail, string priority = "normal")
        => new(title, description, requesterEmail, priority);

    public void AttachJira(string jiraKey)
    {
        if (string.IsNullOrWhiteSpace(jiraKey)) throw new ArgumentException("jiraKey required");
        JiraKey = jiraKey.Trim();
        _history.Add(new TicketHistoryEntry("JIRA_ATTACHED", JiraKey));
    }

    public void MarkInProgress() => TransitionTo(TicketStatus.InProgress, "IN_PROGRESS");
    public void MarkResolved()   => TransitionTo(TicketStatus.Resolved,   "RESOLVED");
    public void MarkClosed()     => TransitionTo(TicketStatus.Closed,     "CLOSED");

    private void TransitionTo(TicketStatus next, string eventName)
    {
        var ok = Status switch
        {
            TicketStatus.New        => next == TicketStatus.InProgress,
            TicketStatus.InProgress => next is TicketStatus.Resolved or TicketStatus.Closed,
            TicketStatus.Resolved   => next == TicketStatus.Closed,
            TicketStatus.Closed     => false,
            _ => false
        };
        if (!ok) throw new InvalidOperationException($"Invalid transition {Status} → {next}");

        Status = next;
        _history.Add(new TicketHistoryEntry(eventName));
    }

    public void AddNote(string note)
    {
        if (!string.IsNullOrWhiteSpace(note))
            _history.Add(new TicketHistoryEntry("NOTE", note));
    }
}
