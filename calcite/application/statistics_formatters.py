def format_shapiro_result(result) -> str:
    text = (
        "Shapiro-Wilk Normality Test Results\n"
        "=========================================\n\n"
        f"Value Column: {result.value_col}\n"
        f"Grouping by: {result.group_name}\n\n"
        "p > 0.05 suggests that the data is normally distributed.\n\n"
        "-----------------------------------------"
    )
    for group in result.groups:
        text += f"\nGroup: {group.group_name} (n={group.sample_size})\n"
        if group.skipped:
            text += "  -> Skipped (sample size < 3)\n"
        else:
            text += f"  - W-statistic: {group.statistic:.4f}\n"
            text += f"  - p-value: {group.p_value:.4f}\n"
            if group.p_value > 0.05:
                text += "  - Conclusion: Data likely follows a normal distribution.\n"
            else:
                text += "  - Conclusion: Data likely does not follow a normal distribution.\n"
        text += "-----------------------------------------"
    return text
