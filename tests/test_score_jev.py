from typesafe_sdk import Score, TypeSafeClient


client = TypeSafeClient()

try:
    while True:
        message = input("Enter a message: ")

        response = client.system_one(
            state=message,
            questions={
                "positivity": Score(
                    instructions="How positive is this message?",
                    criteria=["Negative", "Neutral or mixed", "Positive"],
                )
            },
        )

        answer = response.answers["positivity"]
        winning_score = max(answer.probabilities, key=answer.probabilities.__getitem__)
        winning_label = answer.legend[winning_score]

        print(f"\nMessage: {message}")
        print(f"Score: {answer.score}")
        print(f"Winning label: {winning_label} (score {winning_score})")
        print("\nProbabilities:")
        for score, probability in answer.probabilities.items():
            print(f"{score} - {answer.legend[score]}: {probability}")
        print(f"\nConfidence: {answer.confidence}\n")
except KeyboardInterrupt:
    print("\nExiting.")
