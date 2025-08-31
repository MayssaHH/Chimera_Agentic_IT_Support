namespace Application.Ports;

public enum Decision { Allowed, Denied, RequiresApproval }
public record Citation(string RuleId, string Title, string? Url);