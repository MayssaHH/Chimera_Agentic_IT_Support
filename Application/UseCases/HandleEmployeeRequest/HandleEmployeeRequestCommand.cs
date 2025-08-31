using Application.Ports.Persistence;

namespace Application.UseCases.HandleEmployeeRequest;
using Application.Ports;
using Application.Ports;
using Domain.Tickets;
using MediatR;


public sealed record HandleEmployeeRequestCommand(
    string EmployeeEmail,
    string Text,
    string Priority = "normal"
) : IRequest<AgentResponse>;

public sealed record AgentResponse(
    Guid TicketId,
    string JiraKey,
    Decision Decision,
    IReadOnlyList<string> Checklist,
    IReadOnlyList<Citation> Citations
);
