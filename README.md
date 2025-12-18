# Performance Automation

## Overview
Automated performance testing framework for Deep Security Agent (DSA) rule performance across multiple network scenarios. The pipeline provisions AWS infrastructure, deploys DSM and agents, and measures throughput impact of intrusion prevention rules with/without filter drivers.

## Test Scenarios
- **Server Upload**: Client → Server traffic flow (PCATTCP)
- **Server Download**: Server → Client traffic flow (nginx + hey)
- **Client Download**: Server → Client traffic flow (nginx + hey)

## Architecture

### Infrastructure Components
- **DSM Server**: Deep Security Manager for policy management
- **DSA Instances**: Windows Server 2019 instances with Deep Security Agent
- **Test Machines**: Server and client agents for traffic generation
- **Network**: VPC with security groups configured for test traffic

### Test Flow
```
1. Infrastructure Provisioning (Terraform)
   ├── EC2 instances (Windows Server 2019)
   ├── DSM deployment
   └── Network configuration

2. Agent Setup
   ├── Parallel adapter name preloading
   ├── DSA activation
   └── Filter driver binding verification

3. Performance Testing
   ├── Lightweight warm-up (3 iterations)
   ├── Without Filter Driver baseline
   ├── With Filter Driver (no rules)
   ├── Best case rule (threshold + dependencies)
   └── All rules scenario

4. Results Collection
   ├── HTML report generation
   ├── Bar chart visualization
   └── JFrog artifact upload
```

## Test Methodology

### Baseline Measurements
1. **Without Filter Driver**: Agent disabled, filter driver disabled (20s stabilization)
2. **With Filter Driver**: Agent enabled, filter driver enabled, no rules active (20s stabilization)

### Rule Performance
3. **Best Case Rule**: Threshold rule + dependencies only
4. **All Rules**: Complete rule package or individual rule test

### Traffic Generation
- **Upload Tests**: PCATTCP with 490KB packets, 10 iterations (best 5)
- **Download Tests**: nginx + hey (10 concurrent connections, 100 requests), 20 iterations (best 5)

## Key Features

### Performance Optimizations
- **Parallel Filter Operations**: Enable/disable filters across multiple machines simultaneously
- **Adapter Name Caching**: 1-hour TTL to reduce remote PowerShell calls
- **Efficient Warm-up**: Lightweight 3-iteration warm-up instead of full test cycles
- **Stabilization Waits**: 20s after filter/agent state changes to avoid transient effects

### Test Accuracy
- Warm-up phase to eliminate cold-start bias (DNS, ARP, TCP window)
- 20s stabilization periods after filter state changes
- Multiple iterations with best-case selection
- Consistent test ordering to identify sequence effects

### Error Handling
- Graceful adapter name fallback
- Filter binding presence verification
- Retry logic for sharing violations
- Comprehensive exception logging

## File Structure

```
performance-automation/
├── iac_src/
│   ├── src/
│   │   ├── perf_common.py           # Core utilities, filter management
│   │   ├── perf_individual_rule.py   # Individual rule testing
│   │   ├── perf_package_rule.py      # Rule package testing
│   │   ├── perform_scenario.py       # Main orchestration
│   │   ├── dsm_operation.py          # DSM policy management
│   │   └── backoff_utils.py          # Nginx readiness probing
│   └── templates/                    # DSM policy templates
├── processzone/
│   ├── *.tf                          # Terraform infrastructure
│   └── scripts/                      # PowerShell deployment scripts
├── jenkins/
│   ├── perf_auto_control.groovy      # Main pipeline controller
│   └── performance_test.groovy       # Test execution
└── docker/
    └── Dockerfile                    # Jenkins agent container
```

## Configuration

### Required Parameters
- `--access_key`: AWS access key
- `--secret_key`: AWS secret key
- `--manifest_file`: Infrastructure credentials JSON
- `--dsm_version`: DSM version for policy templates
- `--scenario`: Test scenario (Server_Upload/Server_Download/Client_Download/All)
- `--rule_id`: Rule identifiers to test (comma-separated)
- `--individual_rule_test`: Individual vs package test mode

### Example Usage
```bash
python perform_scenario.py \
  --manifest_file infra_manifest.json \
  --dsm_version 20.0 \
  --scenario Server_Download \
  --rule_id "1005366,1006436" \
  --individual_rule_test true \
  --stats report.html \
  --graph chart.png
```

## Output

### HTML Reports
- Throughput comparison tables (MBps)
- Scenario-based performance breakdown
- Rule identifier tracking
- Best vs average iteration statistics

### Graphs
- Bar charts with scenario comparisons
- Color-coded by test phase
- Throughput in MBps on Y-axis

### Artifacts
- Performance reports uploaded to JFrog
- Test manifests archived
- Console logs with detailed timing

## Important Notes

### Known Limitations
- **Test Ordering Bias**: Sequential tests (Without FD → With FD) may show warm-up advantages in second test
- **Adapter Name Handling**: Spaces in adapter names handled correctly with PowerShell single-quote literals
- **Filter Enforcement**: NIC settings enforcement (RSC/RSS) and cache flushing are currently disabled

### Troubleshooting
- **Adapter name errors**: Check PowerShell string escaping in filter operations
- **Sharing violations**: Automatic retry with 10s backoff
- **Filter binding failures**: Verify Trend Micro LightWeight Filter Driver presence
- **Nginx timeout**: Adaptive probing with exponential backoff (up to 60s)

## Jenkins Pipeline
[Performance Automation Pipeline](https://dsjenkins.trendmicro.com/dslabs/job/Perf-Automation/job/performance-automation/)

## Documentation
- [Development Wiki](https://trendmicro.atlassian.net/wiki/spaces/DSLABS/pages/214934595/Performance+Automation+Development)
- [Rule-Based Testing Plan](https://trendmicro.atlassian.net/wiki/spaces/DSLABS/pages/1020659972/Performance+test+-+Implement+Rule-Based+testing+-+plan)

## Recent Updates
- Implemented parallel filter enable/disable operations
- Added adapter name caching with TTL
- Stabilization waits set to 20s after filter/agent toggles
