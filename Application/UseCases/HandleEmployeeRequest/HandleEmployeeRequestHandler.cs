using Application.Ports; 
using Application.Ports.Persistence;
using Domain.Tickets;
using MediatR;

namespace Application.UseCases.HandleEmployeeRequest;

public sealed class HandleEmployeeRequestHandler
    : IRequestHandler<HandleEmployeeRequestCommand, AgentResponse>
{
    private readonly ITicketRepository _tickets;
    private readonly IClassifierAgent _classifier;
    private readonly IPlannerAgent _planner;
    private readonly IJiraAgent _jira;
    private readonly IExecutorAgent _exec;

    public HandleEmployeeRequestHandler(
        ITicketRepository tickets,
        IClassifierAgent classifier,
        IPlannerAgent planner,
        IJiraAgent jira,
        IExecutorAgent exec)
    {
        _tickets = tickets; _classifier = classifier; _planner = planner;
        _jira = jira; _exec = exec;
    }

    public async Task<AgentResponse> Handle(HandleEmployeeRequestCommand req, CancellationToken ct)
    {
        // 1) Create domain aggregate
        var ticket = Ticket.Create(req.Title, req.Description, req.EmployeeEmail);
        ticket.MarkInProgress();
        await _tickets.AddAsync(ticket, ct);
        await _tickets.SaveAsync(ct);

        // 2) Ask agents (use Description as the problem text)
        var (decision, cites1) = await _classifier.ClassifyAsync(req.Description, ct);
        var (steps,   cites2) = await _planner.PlanAsync(req.Description, ct);

        // 3) Decide priority from the decision (simple rule; tweak as you like)
        var computedPriority = decision switch
        {
            Decision.Allowed           => "normal",
            Decision.Denied            => "low",
            Decision.RequiresApproval  => "high",
            _                          => "normal"
        };

        // If your Ticket has SetPriority(string) (recommended), set it:
        // ticket.SetPriority(computedPriority);

        // 4) Mirror to Jira
        var jiraKey = await _jira.CreateOrAttachAsync(ticket.Title, ticket.Description, computedPriority, ct);
        ticket.AttachJira(jiraKey);

        // 5) Act based on decision
        switch (decision)
        {
            case Decision.Allowed:
                await _exec.EmailChecklistAsync(req.EmployeeEmail, steps, ct);
                await _jira.TransitionAsync(jiraKey, "Resolve Issue", ct);
                ticket.MarkResolved();
                break;

            case Decision.Denied:
                await _jira.AddCommentAsync(jiraKey, "Denied per policy", ct);
                await _jira.TransitionAsync(jiraKey, "Close Issue", ct);
                ticket.MarkClosed();
                break;

            case Decision.RequiresApproval:
                await _exec.NotifyApprovalAsync("approver@company.com", jiraKey, ticket.Title, ct);
                // keep InProgress until approval webhook
                break;
        }

        // 6) Persist & return
        await _tickets.SaveAsync(ct);
        var citations = cites1.Concat(cites2).ToList();

        return new AgentResponse(ticket.Id, jiraKey, decision, steps, citations);
    }
}
