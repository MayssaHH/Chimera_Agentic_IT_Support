namespace Application.Ports;
public interface IClassifierAgent
{
    Task<(Decision Decision, IReadOnlyList<Citation> Citations)>
        ClassifyAsync(string text, CancellationToken ct = default);
}