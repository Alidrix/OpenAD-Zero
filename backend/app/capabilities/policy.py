from app.capabilities.schemas import Capability, CapabilityConfig


def is_lab_available(config: CapabilityConfig) -> bool:
    return config.ctf_lab_mode_enabled


def is_visible(capability: Capability, config: CapabilityConfig) -> bool:
    # Lab capabilities remain visible as a roadmap/configuration item, but are not active.
    return True


def is_executable(capability: Capability, config: CapabilityConfig) -> bool:
    if capability.status != "implemented" or capability.execution != "backend":
        return False
    if capability.mode == "safe":
        return True
    if capability.mode == "assisted":
        return config.assisted_mode_enabled
    if capability.mode == "ctf_lab":
        return config.ctf_lab_mode_enabled and config.advanced_automation_enabled
    return False


def disabled_reason(capability: Capability, config: CapabilityConfig) -> str | None:
    if is_executable(capability, config):
        return None
    if capability.status != "implemented":
        return f"Capability status is {capability.status}."
    if capability.execution != "backend":
        return f"Execution mode {capability.execution} is not backend-executable."
    if capability.mode == "assisted" and not config.assisted_mode_enabled:
        return "Assisted mode is disabled by configuration."
    if capability.mode == "ctf_lab" and not config.ctf_lab_mode_enabled:
        return "CTF/Lab Mode is disabled by configuration."
    if capability.mode == "ctf_lab" and not config.advanced_automation_enabled:
        return "Advanced automation is disabled by configuration."
    return "Capability is not executable under the current policy."
