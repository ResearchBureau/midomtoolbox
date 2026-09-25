"""Generating best-fit MIDOM protocols from possibly unstructured text

Why? A common question in deidentification is "Does our deidentification procedure
remove all tags from the following list" Or "Does it keep all these?" In both cases
the list in question is often just copy-pasted into an email or hand-typed.

To answer this question you would load your procedure from a structured MIDOM protocol
json file, create a second protocol corresponding to the question (list of KEEP and
or REMOVE list) and then compare them programmatically.

Creating a MIDOM protocol from scratch is annoying. It would be useful to quickly
extract the required info from a semi-structured list.

"""
