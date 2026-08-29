import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination } from "swiper/modules";
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";

interface ImageSliderProps {
  images: string[];
  variant?: "default" | "banner";
}

export function ImageSlider({ images, variant = "default" }: ImageSliderProps) {
  const swiperRef = useRef<any>(null);
  const [failed, setFailed] = useState<Set<string>>(() => new Set());
  useEffect(() => setFailed(new Set()), [images]);
  const visibleImages = images.filter((image) => image && !failed.has(image));
  const showNav = visibleImages.length > 1;

  if (visibleImages.length === 0) return null;

  return (
    <div className={variant === "banner" ? "flex h-full w-full justify-center" : "my-2 flex justify-center px-3 pb-4"}>
      <div className={`relative w-full ${variant === "banner" ? "h-full max-w-none" : "max-w-[640px]"}`}>
        <Swiper
          modules={[Navigation, Pagination]}
          onSwiper={(swiper) => (swiperRef.current = swiper)}
          slidesPerView={1}
          spaceBetween={12}
          pagination={{ clickable: true }}
          loop={showNav}
        >
          {visibleImages.map((img, index) => (
            <SwiperSlide key={img}>
              <img
                src={img}
                alt={`Destination view ${index + 1}`}
                className={variant === "banner"
                  ? "h-44 w-full bg-gradient-to-br from-teal-50 via-sky-50 to-amber-50 object-cover sm:h-52 dark:from-teal-950/40 dark:via-sky-950/30 dark:to-amber-950/20"
                  : "h-52 w-full rounded-xl bg-slate-100 object-cover sm:h-64 dark:bg-slate-900"}
                loading="lazy"
                decoding="async"
                referrerPolicy="no-referrer"
                onError={() => setFailed((current) => new Set(current).add(img))}
              />
            </SwiperSlide>
          ))}
        </Swiper>

        {showNav && (
          <>
            <button
              onClick={() => swiperRef.current?.slidePrev()}
              aria-label="Previous"
              className="absolute left-2 top-1/2 z-10 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/40 bg-black/55 text-white shadow-md backdrop-blur-sm hover:bg-black/75"
            >
              <ChevronLeft className="text-[9px]" />
            </button>
            <button
              onClick={() => swiperRef.current?.slideNext()}
              aria-label="Next"
              className="absolute right-2 top-1/2 z-10 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/40 bg-black/55 text-white shadow-md backdrop-blur-sm hover:bg-black/75"
            >
              <ChevronRight className="text-[9px]" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
