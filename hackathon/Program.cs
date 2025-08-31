using MediatR;
using Microsoft.EntityFrameworkCore;

// Application
using Application.UseCases.HandleEmployeeRequest;
using Application.Ports.Persistence;
using Application.Ports;

// Infrastructure
using Persistence;                  // AppDbContext, EfTicketRepository
using External;      // HttpClassifierAgent, HttpPlannerAgent, HttpJiraAgent, HttpExecutorAgent

var builder = WebApplication.CreateBuilder(args);
var cfg = builder.Configuration;

// ---------- Services ----------

// Controllers + Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// CORS (adjust origin to match your frontend)
const string Cors = "Front";
builder.Services.AddCors(o => o.AddPolicy(Cors, p =>
    p.WithOrigins("http://localhost:3000")
     .AllowAnyHeader()
     .AllowAnyMethod()));

// EF Core (PostgreSQL)
builder.Services.AddDbContext<AppDbContext>(opts =>
    opts.UseNpgsql(cfg.GetConnectionString("DefaultConnection"))
        .EnableDetailedErrors()
        .EnableSensitiveDataLogging());

// Repositories
builder.Services.AddScoped<ITicketRepository, EfTicketRepository>();

// MediatR (scan Application assembly for handlers)
builder.Services.AddMediatR(m =>
    m.RegisterServicesFromAssembly(typeof(HandleEmployeeRequestHandler).Assembly));

// ---------- Agents: connect to Python service ----------
var agentsBase = cfg["Agents:BaseUrl"] ?? "http://localhost:8000";
var agentsApiKey = cfg["Agents:ApiKey"];

void ConfigureAgentClient(HttpClient c)
{
    c.BaseAddress = new Uri(agentsBase);
    if (!string.IsNullOrWhiteSpace(agentsApiKey))
        c.DefaultRequestHeaders.Add("x-api-key", agentsApiKey);
    c.Timeout = TimeSpan.FromSeconds(15);
}

// Typed HTTP clients (adapters in Infrastructure/External)
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

app.Run();
