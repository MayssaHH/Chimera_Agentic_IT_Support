using System.Net.Http.Headers;
using Application.Ports;
using MediatR;
using Microsoft.EntityFrameworkCore;

// Application layer (handlers, ports)
using Application.UseCases.HandleEmployeeRequest;
using Application.Ports.Persistence;
using Application.Ports;

// Infrastructure implementations
using Persistence;                 // AppDbContext, EfTicketRepository
using External;     // HttpClassifierAgent, HttpPlannerAgent, HttpJiraAgent, HttpExecutorAgent

var builder = WebApplication.CreateBuilder(args);
var cfg = builder.Configuration;


// Controllers + Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// CORS (adjust origin as needed)
const string Cors = "Front";
builder.Services.AddCors(o => o.AddPolicy(Cors, p =>
    p.WithOrigins("http://localhost:3000")   // your frontend origin
     .AllowAnyHeader()
     .AllowAnyMethod()));

// EF Core (PostgreSQL)
builder.Services.AddDbContext<AppDbContext>(opts =>
    opts.UseNpgsql(cfg.GetConnectionString("DefaultConnection"))
        .EnableDetailedErrors()
        .EnableSensitiveDataLogging());

// Repositories
builder.Services.AddScoped<ITicketRepository, EfTicketRepository>();

// MediatR (register Application handlers)
builder.Services.AddMediatR(m =>
    m.RegisterServicesFromAssembly(typeof(HandleEmployeeRequestHandler).Assembly));

// Agents base URL / key from config
var agentsBase = cfg["Agents:BaseUrl"] ?? "http://localhost:8000";
var agentsApiKey = cfg["Agents:ApiKey"];

// Helper to set base + optional x-api-key
void ConfigureAgentClient(HttpClient c)
{
    c.BaseAddress = new Uri(agentsBase);
    if (!string.IsNullOrWhiteSpace(agentsApiKey))
        c.DefaultRequestHeaders.Add("x-api-key", agentsApiKey);
    c.Timeout = TimeSpan.FromSeconds(10);
    c.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
}

// Typed HTTP clients to Python service (Option A)
builder.Services.AddHttpClient<IClassifierAgent, HttpClassifierAgent>(ConfigureAgentClient);
builder.Services.AddHttpClient<IPlannerAgent,   HttpPlannerAgent>(ConfigureAgentClient);
builder.Services.AddHttpClient<IJiraAgent,      HttpJiraAgent>(ConfigureAgentClient);
builder.Services.AddHttpClient<IExecutorAgent,  HttpExecutorAgent>(ConfigureAgentClient);

var app = builder.Build();

// ---------- Pipeline ----------

app.UseSwagger();
app.UseSwaggerUI();

app.UseCors(Cors);
app.MapControllers();

// Simple health check for agents (optional)
app.MapGet("/health/agents", async (IHttpClientFactory factory) =>
{
    try
    {
        var http = factory.CreateClient(nameof(IClassifierAgent)); // any of the typed clients will do
        var resp = await http.GetAsync("/health");
        return Results.Json(new { ok = resp.IsSuccessStatusCode, status = (int)resp.StatusCode });
    }
    catch (Exception ex)
    {
        return Results.Json(new { ok = false, error = ex.Message }, statusCode: 503);
    }
});

app.Run();
