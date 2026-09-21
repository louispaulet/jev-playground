from typesafe_sdk import Noul, TypeSafeClient


client = TypeSafeClient()

try:
    while True:
        message = input("Enter a message: ")

        response = client.system_one(
            state=message,
            questions={
                "urgency": Noul(
                    instructions="Does this message express urgency?",
                )
            },
        )

        answer = response.answers["urgency"]

        print(f"\nMessage: {message}")
        print(f"Urgency probability: {answer.noul}\n")
except KeyboardInterrupt:
    print("\nExiting.")
