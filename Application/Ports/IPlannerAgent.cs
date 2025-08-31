namespace Application.Ports;

public interface IPlannerAgent
{
    Task<(IReadOnlyList<string> Steps, IReadOnlyList<Citation> Citations)>
        PlanAsync(string text, CancellationToken ct = default);
}