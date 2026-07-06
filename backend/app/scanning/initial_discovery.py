from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.parameter_validation import ParameterValidationError, validate_network_value, validate_output_param

SAFE_INITIAL_DISCOVERY_PROFILE = 'safe_default'
ALLOWED_NMAP_ARGS = ('-Pn', '-sV', '--top-ports', '1000')


@dataclass(frozen=True)
class InitialDiscoveryCommand:
    tool: str
    args: list[str]
    output_xml: Path
    targets: list[str]


def validate_initial_discovery_profile(profile: str) -> str:
    if profile != SAFE_INITIAL_DISCOVERY_PROFILE:
        raise ParameterValidationError('initial discovery profile is not allowed')
    return profile


def validate_initial_discovery_targets(targets: list[str]) -> list[str]:
    if not targets:
        raise ParameterValidationError('validated scope is required')
    validated: list[str] = []
    for target in targets:
        validated.extend(
            validate_network_value(
                'targets',
                target,
                targets,
                allow_hostnames=False,
                allow_urls=False,
                max_cidr_prefix=16,
            )
        )
    return list(dict.fromkeys(validated))


def build_safe_nmap_command(
    *, targets: list[str], job_dir: Path, profile: str = SAFE_INITIAL_DISCOVERY_PROFILE
) -> InitialDiscoveryCommand:
    validate_initial_discovery_profile(profile)
    job_dir = Path(job_dir).resolve(strict=False)
    output_xml = Path(validate_output_param('output', 'nmap.xml', job_dir=str(job_dir), allowed_extensions=['.xml']))
    validated_targets = validate_initial_discovery_targets(targets)
    args = ['-Pn', '-sV', '--top-ports', '1000', '-oX', str(output_xml), *validated_targets]
    return InitialDiscoveryCommand(tool='nmap', args=args, output_xml=output_xml, targets=validated_targets)


def masked_command(command: InitialDiscoveryCommand) -> str:
    return ' '.join([command.tool, *command.args])
