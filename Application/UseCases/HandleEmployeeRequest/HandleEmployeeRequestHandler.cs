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
        var ticket = Ticket.Create("Employee Support Request", req.Text, req.EmployeeEmail, req.Priority);
        ticket.MarkInProgress();
        await _tickets.AddAsync(ticket, ct);
        await _tickets.SaveAsync(ct);

        var (decision, cites1) = await _classifier.ClassifyAsync(req.Text, ct);
        var (steps,   cites2) = await _planner.PlanAsync(req.Text, ct);

        var jiraKey = await _jira.CreateOrAttachAsync(ticket.Title, ticket.Description, req.Priority, ct);
        ticket.AttachJira(jiraKey);

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
                break;
        }

        await _tickets.SaveAsync(ct);
        var citations = cites1.Concat(cites2).ToList();
        return new AgentResponse(ticket.Id, jiraKey, decision, steps, citations);
    }
}
