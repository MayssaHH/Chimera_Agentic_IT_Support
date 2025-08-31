using Application.Ports;
using Application.Ports.Persistence;
using External;
using Microsoft.EntityFrameworkCore;
using Persistence;
using MediatR;
using Application.UseCases.HandleEmployeeRequest; // for type discovery

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// EF Core
builder.Services.AddDbContext<AppDbContext>(opts =>
    opts.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));


builder.Services.AddMediatR(cfg =>
    cfg.RegisterServicesFromAssembly(typeof(HandleEmployeeRequestHandler).Assembly));

builder.Services.AddScoped<IJiraAgent, NoopJiraAgent>();
builder.Services.AddScoped<IExecutorAgent, NoopExecutorAgent>();


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