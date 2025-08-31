using Application.UseCases.HandleEmployeeRequest;
using MediatR;
using Microsoft.AspNetCore.Mvc;

namespace hackathon.Controllers;

[ApiController]
[Route("api/[controller]")]
public class RequestsController : ControllerBase
{
    private readonly IMediator _mediator;

    public RequestsController(IMediator mediator) => _mediator = mediator;

    /// <summary>
    /// Submit a new IT support request
    /// </summary>
    [HttpPost]
    public async Task<IActionResult> Post([FromBody] HandleEmployeeRequestCommand cmd, CancellationToken ct)
    {
        var response = await _mediator.Send(cmd, ct);
        return Ok(response);
    }
}