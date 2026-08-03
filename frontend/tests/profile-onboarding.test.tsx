import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProfileForm } from "@/features/onboarding/profile-form";
import { renderWithQuery } from "@/tests/utils";

const { createProfile, push } = vi.hoisted(() => ({
  createProfile: vi.fn(),
  push: vi.fn(),
}));

vi.mock("@/lib/api/client", () => ({
  api: { createProfile },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

describe("profile onboarding", () => {
  beforeEach(() => {
    createProfile.mockReset();
    push.mockReset();
    createProfile.mockResolvedValue({
      id: "10000000-0000-4000-8000-000000000099",
    });
  });

  it("adds multi-word profile details and submits them", async () => {
    renderWithQuery(<ProfileForm />);

    fireEvent.change(screen.getByRole("textbox", { name: "Name" }), {
      target: { value: "Mina" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    await screen.findByRole("heading", { name: "Situation" });

    fireEvent.change(screen.getByRole("textbox", { name: "Current city" }), {
      target: { value: "Milan" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Current role" }), {
      target: { value: "AI engineer" },
    });
    fireEvent.change(screen.getByRole("textbox", { name: "Education" }), {
      target: { value: "MSc in Computer Science" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    await screen.findByRole("heading", { name: "Goals" });

    const goalInput = screen.getByRole("textbox", { name: "New goal" });
    fireEvent.change(goalInput, {
      target: { value: "Build an AI company" },
    });
    expect(goalInput).toHaveValue("Build an AI company");
    fireEvent.click(
      within(goalInput.parentElement!).getByRole("button", { name: "Add" }),
    );
    expect(screen.getByText("Build an AI company")).toBeInTheDocument();

    const interestInput = screen.getByRole("textbox", {
      name: "New interest",
    });
    fireEvent.change(interestInput, {
      target: { value: "Human robot interaction" },
    });
    fireEvent.keyDown(interestInput, { key: "Enter" });
    expect(screen.getByText("Human robot interaction")).toBeInTheDocument();

    for (const heading of [
      "Strengths",
      "Constraints",
      "Statistics",
      "Review",
    ]) {
      fireEvent.click(screen.getByRole("button", { name: "Continue" }));
      expect(
        await screen.findByRole("heading", { name: heading }),
      ).toBeInTheDocument();
    }

    const submitButton = screen.getByRole("button", {
      name: "Choose a decision",
    });
    expect(submitButton).toBeEnabled();
    fireEvent.click(submitButton);

    await waitFor(() => expect(createProfile).toHaveBeenCalledOnce());
    expect(createProfile).toHaveBeenCalledWith(
      expect.objectContaining({
        goals: ["Build an AI company"],
        interests: ["Human robot interaction"],
      }),
    );
    expect(push).toHaveBeenCalledWith(
      "/scenario?profile=10000000-0000-4000-8000-000000000099",
    );
  });
});
