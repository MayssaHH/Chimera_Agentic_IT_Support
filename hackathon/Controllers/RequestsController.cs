namespace hackathon.Controllers;

using Application.UseCases.HandleEmployeeRequest;
using MediatR;
using Microsoft.AspNetCore.Mvc;


[ApiController]
[Route("api/[controller]")]
public class RequestsController : ControllerBase
{
    private readonly IMediator _mediator;
    public RequestsController(IMediator mediator) => _mediator = mediator;

    [HttpPost]
    public async Task<IActionResult> Post([FromBody] HandleEmployeeRequestCommand cmd, CancellationToken ct)
    {
        var response = await _mediator.Send(cmd, ct);
        return Ok(response);
    }



    [HttpGet("ping")]
    public IActionResult Ping() => Ok("API is alive ✅");
}