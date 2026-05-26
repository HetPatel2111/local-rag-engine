type Props = {
  size?: number;
};

export default function LoadingSpinner({ size = 18 }: Props) {
  return (
    <span
      className="spinner"
      style={{ width: size, height: size }}
      aria-hidden="true"
    />
  );
}

