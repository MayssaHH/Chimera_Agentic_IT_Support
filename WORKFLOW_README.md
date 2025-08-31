# IT Support Workflow System

This system implements an automated IT support workflow that processes employee requests through multiple AI agents, following company policies and rules.

## Workflow Overview

The system follows this sequence:

1. **📚 Retrieve** - Gather relevant company policies and procedures
2. **🔄 Router** - Evaluate request complexity and select appropriate AI model
3. **🎯 Classifier** - Make decision based on policy compliance (ALLOWED/DENIED/REQUIRES_APPROVAL)
4. **🔧 JIRA Agent** - Create ticket and manage status throughout workflow
5. **👥 HIL** - Human-in-the-loop for approval when needed
6. **📋 Planner** - Create execution plan for approved requests
7. **🛠️ IT Agent** - Execute the plan using available tools
8. **✅ Closer** - Complete request and generate satisfaction survey

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_simple.txt
```

### 2. Run the Test Workflow

```bash
python test_workflow_simple.py
```

This will run a complete workflow simulation with a software installation request.

## What You'll See

The system provides comprehensive logging throughout the workflow:

- **📚 RETRIEVE NODE** - Document retrieval and policy analysis
- **🔄 ROUTER NODE** - Complexity evaluation and model selection
- **🎯 CLASSIFIER NODE** - Policy compliance decision making
- **🔧 JIRA AGENT NODE** - Ticket creation and status management
- **👥 HIL NODE** - Human approval workflow management
- **📋 PLANNER NODE** - Execution plan creation
- **🛠️ IT AGENT NODE** - Plan execution and tool usage
- **✅ CLOSER NODE** - Request completion and survey generation

## Example Request

The test workflow uses this sample request:

```
Title: Software Installation Request
Description: Need Visual Studio Code installed on my development machine for Python development
Category: software_installation
Priority: MEDIUM
Employee: John Doe (Engineering)
```

## Expected Workflow Path

1. **Classification**: ALLOWED (standard development tool)
2. **JIRA Ticket**: Created and moved to "In Progress"
3. **Planning**: Execution plan created
4. **Execution**: IT agent performs installation
5. **Completion**: Ticket moved to "Done", request closed

## Configuration

The system uses mock services by default for testing. To use real services:

1. Set environment variables for JIRA/SMTP
2. Update `src/config.py` with your settings
3. Set `USE_MOCK_SERVICES=false`

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root directory
2. **Missing Dependencies**: Install requirements with `pip install -r requirements_simple.txt`
3. **Mock Services**: The system uses mock services by default - check logs for "MOCK" messages

### Debug Mode

Set `DEBUG=true` in environment or config to see detailed logging.

## Architecture

- **Nodes**: Each workflow step is implemented as a node function
- **State**: Workflow state is passed between nodes as a dictionary
- **Mock Services**: JIRA, email, and other services are mocked for testing
- **Logging**: Comprehensive logging tracks every step of the workflow

## Next Steps

1. **Customize Policies**: Update the sample policies in the test data
2. **Add Real Services**: Configure JIRA, SMTP, and other external services
3. **Extend Workflow**: Add new nodes for specific business processes
4. **Production Deployment**: Use LangGraph for production workflow orchestration
