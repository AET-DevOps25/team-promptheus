package com.autoback.autoback.CommunicationObjects;

import java.util.List;

public record SelectionSubmission(
        List<Long> selection
) {}
