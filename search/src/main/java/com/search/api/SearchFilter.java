package com.search.api;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Utility class for handling search filter operations and validation
 */
public class SearchFilter {
    public static final List<String> FILTERABLE_ATTRIBUTES = Arrays.asList(
        "user",
        "week",
        "contribution_type",
        "repository",
        "author",
        "created_at_timestamp",
        "is_selected"
    );

    public static final List<String> SORTABLE_ATTRIBUTES = Arrays.asList(
        "created_at_timestamp",
        "relevance_score"
    );

    public static final List<String> TIMESTAMP_ATTRIBUTES = Arrays.asList(
        "created_at_timestamp"
    );

    public static final List<String> BOOLEAN_ATTRIBUTES = Arrays.asList(
        "is_selected"
    );

    /**
     * Builds a MeiliSearch filter string from a usercode and filter map
     *
     * @param usercode The user's UUID for repo filtering
     * @param filters Map of filter attributes and values
     * @return Formatted filter string for MeiliSearch
     */
    public static String buildFilterString(Map<String, String> filters) {
        StringBuilder filterBuilder = new StringBuilder();
        if (filters != null && !filters.isEmpty()) {
            for (Map.Entry<String, String> filter : filters.entrySet()) {
                String attribute = filter.getKey();
                String value = filter.getValue();

                // Validate that the attribute is filterable
                if (FILTERABLE_ATTRIBUTES.contains(attribute)) {
                    filterBuilder.append(" AND ");
                    appendFilterCondition(filterBuilder, attribute, value);
                }
            }
        }

        return filterBuilder.toString();
    }

    /**
     * Validates and filters sort fields to only include sortable attributes
     *
     * @param sortFields List of sort field specifications
     * @return Array of valid sort fields
     */
    public static String[] validateAndFilterSortFields(List<String> sortFields) {
        if (sortFields == null || sortFields.isEmpty()) {
            return new String[0];
        }

        return sortFields
            .stream()
            .filter(s -> {
                String sortField = s.startsWith("-") ? s.substring(1) : s;
                return SORTABLE_ATTRIBUTES.contains(sortField);
            })
            .toArray(String[]::new);
    }

    /**
     * Validates a filter value based on the attribute type
     *
     * @param attribute The attribute name
     * @param value The value to validate
     * @return true if the value is valid for the attribute type
     */
    public static boolean isValidFilterValue(String attribute, String value) {
        if (value == null || value.trim().isEmpty()) {
            return false;
        }

        if (BOOLEAN_ATTRIBUTES.contains(attribute)) {
            return "true".equalsIgnoreCase(value) || "false".equalsIgnoreCase(value);
        }

        if (TIMESTAMP_ATTRIBUTES.contains(attribute)) {
            // Accept single timestamps or ranges (e.g., "1640995200" or "1640995200 TO 1672531200")
            return value.matches("\\d+") || value.matches("\\d+\\s+TO\\s+\\d+");
        }

        // For string attributes, any non-empty value is valid
        return true;
    }

    /**
     * Sanitizes a filter value to prevent injection attacks
     *
     * @param value The value to sanitize
     * @return Sanitized value
     */
    public static String sanitizeFilterValue(String value) {
        if (value == null) {
            return null;
        }

        // Remove potentially dangerous characters for MeiliSearch filters
        return value.replaceAll("[\"\\\\]", "").trim();
    }

    /**
     * Appends a filter condition to the filter builder based on attribute type
     *
     * @param filterBuilder The StringBuilder to append to
     * @param attribute The attribute name
     * @param value The filter value
     */
    private static void appendFilterCondition(StringBuilder filterBuilder, String attribute, String value) {
        String sanitizedValue = sanitizeFilterValue(value);

        if (!isValidFilterValue(attribute, sanitizedValue)) {
            return; // Skip invalid values
        }

        if (TIMESTAMP_ATTRIBUTES.contains(attribute)) {
            if (sanitizedValue.contains("TO")) {
                // Range filter format: "1640995200 TO 1672531200"
                filterBuilder.append(attribute).append(" ").append(sanitizedValue);
            } else {
                // Specific timestamp
                filterBuilder.append(attribute).append(" = ").append(sanitizedValue);
            }
        } else if (BOOLEAN_ATTRIBUTES.contains(attribute)) {
            // Boolean filter
            filterBuilder.append(attribute).append(" = ").append(sanitizedValue.toLowerCase());
        } else {
            // String filters
            filterBuilder.append(attribute).append(" = \"").append(sanitizedValue).append("\"");
        }
    }

    /**
     * Creates a filter map from individual filter parameters
     *
     * @param user User filter
     * @param week Week filter
     * @param contributionType Contribution type filter
     * @param repository Repository filter
     * @param author Author filter
     * @param createdAtTimestamp Timestamp filter
     * @param isSelected Selection status filter
     * @return Map of non-null filters
     */
    public static Map<String, String> createFilterMap(
        String user,
        String week,
        String contributionType,
        String repository,
        String author,
        String createdAtTimestamp,
        Boolean isSelected
    ) {
        Map<String, String> filters = new java.util.HashMap<>();

        if (user != null && !user.trim().isEmpty()) filters.put("user", user.trim());
        if (week != null && !week.trim().isEmpty()) filters.put("week", week.trim());
        if (contributionType != null && !contributionType.trim().isEmpty()) filters.put("contribution_type", contributionType.trim());
        if (repository != null && !repository.trim().isEmpty()) filters.put("repository", repository.trim());
        if (author != null && !author.trim().isEmpty()) filters.put("author", author.trim());
        if (createdAtTimestamp != null && !createdAtTimestamp.trim().isEmpty()) filters.put("created_at_timestamp", createdAtTimestamp.trim());
        if (isSelected != null) filters.put("is_selected", isSelected.toString());

        return filters;
    }
}
