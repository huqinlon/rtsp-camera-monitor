---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 30460221009af297ae64970e92016091ad93adb158f79ff0668429d8ce7ed9c50f4a549f9c022100b81ad6d91d6fc5a2ac31a084907ae0e602ecf0a1d84809b6a7e4a665c885f45f
    ReservedCode2: 3046022100db884a23b5a2ccca34082c334ec53edfe990bb34e1963374e7e5c6ae687e8fbb022100d975b50793540d8dc7a6a19f48622efaa6d42442dbe3b7c54af92596ebd89a16
---

name: Pull Request
description: Submit changes to the project
title: "[PR] "
labels: []
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        ## Pull Request

        Thanks for submitting a pull request!

        Please fill out this template to help us review your changes.

  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear description of what your PR does
      placeholder: Describe your changes...
    validations:
      required: true

  - type: textarea
    id: motivation
    attributes:
      label: Motivation
      description: Why is this change necessary?
      placeholder: This change is necessary because...

  - type: textarea
    id: changes
    attributes:
      label: Changes Made
      description: List the files changed and why
      placeholder: |
        - file1.py: Added new function
        - file2.py: Modified existing function
        - config.json: Updated default values

  - type: textarea
    id: testing
    attributes:
      label: Testing
      description: How has this been tested?
      placeholder: |
        - Unit tests added
        - Manual testing performed
        - Docker image built successfully

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots (if applicable)
      description: Any screenshots showing the changes
      placeholder: Add screenshots here...

  - type: textarea
    id: checklist
    attributes:
      label: Checklist
      description: Make sure all items are checked
      value: |
        - [ ] My code follows the project's code style
        - [ ] I have performed a self-review of my code
        - [ ] I have commented my code, particularly in hard-to-understand areas
        - [ ] My changes generate no new warnings
        - [ ] I have added tests that prove my fix is effective or my feature works
        - [ ] New and existing unit tests pass locally with my changes
        - [ ] I have updated the documentation

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Any additional context about your PR
      placeholder: Additional context...
