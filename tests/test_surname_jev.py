from typesafe_sdk import Choice, TypeSafeClient


client = TypeSafeClient()

try:
    while True:
        surname = input("Enter a surname: ")

        response = client.system_one(
            state=surname,
            questions={
                "gender": Choice(
                    instructions="Based only on the surname, what is the gender of this person?",
                    criteria={
                        "male": "male",
                        "female": "female",
                        "unisex": "unisex",
                    },
                )
            },
        )

        answer = response.answers["gender"]

        print(f"\nSurname: {surname}")
        print(f"Guess: {answer.choice}")
        print("\nProbabilities:")
        for choice, probability in answer.probabilities.items():
            print(f"{choice}: {probability}")
        print(f"\nConfidence: {answer.confidence}\n")
except KeyboardInterrupt:
    print("\nExiting.")
