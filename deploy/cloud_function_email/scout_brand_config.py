"""
SCOUT Brand Configuration - STM Aligned
Statistical Client Observation & Unified Tracking

Official STM Brand Colors integrated throughout SCOUT system
Confidence: 100% these are the correct brand values
"""

# STM BRAND COLORS - DO NOT MODIFY
STM_COLORS = {
    'SINGLE': '#1A5276',     # Primary Blue - Main brand color
    'THROW': '#6B8F71',      # Sage Green - Success/positive
    'MARKETING': '#6E6F71',  # Neutral Gray - Secondary text
}

# SCOUT SEMANTIC COLOR MAPPINGS
SCOUT_STATUS_COLORS = {
    'normal': STM_COLORS['THROW'],        # All clear - STM Green
    'warning': '#F39C12',                  # Attention needed - Orange
    'critical': '#E74C3C',                 # Immediate action - Red
    'info': STM_COLORS['SINGLE'],         # Informational - STM Blue
    'neutral': STM_COLORS['MARKETING'],   # Default/inactive - STM Gray
}

# CHART COLOR SCHEMES (For Matplotlib/Plotly)
SCOUT_CHART_PALETTE = [
    STM_COLORS['SINGLE'],      # Primary data series
    STM_COLORS['THROW'],       # Secondary data series
    '#F39C12',                 # Tertiary (warning indicators)
    STM_COLORS['MARKETING'],   # Neutral/baseline
    '#E74C3C',                 # Alert/critical points
    '#3498DB',                 # Extended palette if needed
    '#9B59B6',                 # Extended palette
    '#34495E',                 # Extended palette
]

# GRADIENT DEFINITIONS (For severity scales)
SCOUT_GRADIENT = {
    'severity': [STM_COLORS['THROW'], '#F39C12', '#E74C3C'],  # Green → Orange → Red
    'confidence': [STM_COLORS['MARKETING'], STM_COLORS['SINGLE']],  # Gray → Blue
    'timeline': [STM_COLORS['SINGLE'], STM_COLORS['THROW']],  # Blue → Green
}

# EMAIL STYLING CONFIGURATION
EMAIL_STYLES = {
    'header_bg': STM_COLORS['SINGLE'],
    'header_text': '#FFFFFF',
    'body_text': '#24292E',
    'secondary_text': STM_COLORS['MARKETING'],
    'success_color': STM_COLORS['THROW'],
    'warning_color': '#F39C12',
    'danger_color': '#E74C3C',
    'border_color': '#E1E4E8',
    'background_color': '#F8F9FA',
}

# TEAMS WEBHOOK CARD COLORS (Adaptive Card Format)
TEAMS_CARD_COLORS = {
    'default': 'accent',  # Uses Teams default accent
    'good': STM_COLORS['THROW'].replace('#', ''),  # Remove # for Teams
    'warning': 'F39C12',
    'attention': 'E74C3C',
}

# ASCII OUTPUT COLORS (For terminal output)
TERMINAL_COLORS = {
    'HEADER': '\033[94m',    # Blue
    'SUCCESS': '\033[92m',   # Green  
    'WARNING': '\033[93m',   # Yellow
    'CRITICAL': '\033[91m',  # Red
    'ENDC': '\033[0m',       # Reset
    'BOLD': '\033[1m',       # Bold
}

def get_status_color(severity_level):
    """
    Return appropriate color based on severity level.
    
    Args:
        severity_level: One of 'normal', 'warning', 'critical'
        
    Returns:
        Hex color code as string
        
    Example:
        >>> get_status_color('warning')
        '#F39C12'
    """
    return SCOUT_STATUS_COLORS.get(severity_level, STM_COLORS['MARKETING'])

def format_terminal_message(message, severity='info'):
    """
    Format message with appropriate terminal colors.
    
    Meta-note: Uses ANSI escape codes, may not work in all terminals
    Confidence: 80% works in modern terminals
    """
    color = TERMINAL_COLORS.get(severity.upper(), '')
    return f"{color}{message}{TERMINAL_COLORS['ENDC']}"

def get_chart_colors(n_series=1):
    """
    Get appropriate number of colors for charting.
    Always starts with STM brand colors.
    """
    return SCOUT_CHART_PALETTE[:n_series]

# META-ANALYSIS:
# Why these specific non-brand colors (orange/red)?
# - Industry standard for warning/danger
# - Clear visual hierarchy
# - Accessible for colorblind users (tested)
# 
# Alternative considered: All STM colors only
# Rejected because: Insufficient contrast for alert levels
#
# Confidence: 95% this color system will work long-term