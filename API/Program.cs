using Application.Ports;
using Application.Ports.Agents;
using Application.Ports.Persistence;
using External;    // your HTTP agents/Jira/Email
using Persistence; // AppDbContext, EfTicketRepository
using Microsoft.EntityFrameworkCore;
using Persistence;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// EF Core
builder.Services.AddDbContext<AppDbContext>(o =>
    o.UseSqlite(builder.Configuration.GetConnectionString("Default")));

// Persistence port -> Infra implementation
builder.Services.AddScoped<ITicketRepository, EfTicketRepository>();

// Agent ports -> Infra implementations (examples)
builder.Services.AddHttpClient<IClassifierAgent, HttpClassifierAgent>(c =>
    c.BaseAddress = new Uri(builder.Configuration["Agents:BaseUrl"]!));
builder.Services.AddHttpClient<IPlannerAgent, HttpPlannerAgent>(c =>
    c.BaseAddress = new Uri(builder.Configuration["Agents:BaseUrl"]!));
// builder.Services.AddScoped<IJiraAgent, JiraAgent>();
// builder.Services.AddScoped<IExecutorAgent, SmtpExecutorAgent>();

var app = builder.Build();

app.UseSwagger(); app.UseSwaggerUI();
app.MapControllers();
app.Run();